from datetime import datetime, timedelta
from time import time
from collections import defaultdict
import sqlite3
import signal

old_db = sqlite3.connect("..\\NewSquadsMonitor\\squads.sqlite")
old_db.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
# old_db.row_factory = sqlite3.Row

new_db = sqlite3.connect('jubilant-system.sqlite')
new_db.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
# new_db.row_factory = sqlite3.Row


class QUERIES:
    class NEW:
        SCHEMA = ''.join(open('sql\\schema.sql', mode='r').readlines())

        CREATE_OPERATION_ID = 'insert into operations_info (squad_id, timestamp) values (:squad_id, :timestamp);'
        GET_OPERATION_ID = 'select operation_id from operations_info order by operation_id desc limit 1;'

        INSERT_DELETED_SQUAD = 'insert into squadrons_deleted (operation_id, squad_id) VALUES (:operation_id, :squad_id);'
        IS_DELETED = 'select count(*) as deleted from squadrons_deleted where squad_id = :squad_id;'

        INSERT_INFO = """INSERT INTO squadrons_historical_data (
operation_id,
name,
tag,
owner_name,
owner_id,
platform,
created,
created_ts,
accepting_new_members,
power_id,
power_name,
superpower_id,
superpower_name,
faction_id,
faction_name,
user_tags,
member_count,
pending_count,
"full", 
public_comms,
public_comms_override,
public_comms_available,
current_season_trade_score,
previous_season_trade_score,
current_season_combat_score,
previous_season_combat_score,
current_season_exploration_score,
previous_season_exploration_score,
current_season_cqc_score,
previous_season_cqc_score,
current_season_bgs_score,
previous_season_bgs_score,
current_season_powerplay_score,
previous_season_powerplay_score,
current_season_aegis_score,
previous_season_aegis_score
) values (
:operation_id,
:name,
:tag,
:owner_name,
:owner_id,
:platform,
:created,
:created_ts,
:accepting_new_members,
:power_id,
:power_name,
:super_power_id,
:super_power_name,
:faction_id,
:faction_name,
:user_tags,
:member_count,
:pending_count,
:full, 
:public_comms,
:public_comms_override,
:public_comms_available,
:current_season_trade_score,
:previous_season_trade_score,
:current_season_combat_score,
:previous_season_combat_score,
:current_season_exploration_score,
:previous_season_exploration_score,
:current_season_cqc_score,
:previous_season_cqc_score,
:current_season_bgs_score,
:previous_season_bgs_score,
:current_season_powerplay_score,
:previous_season_powerplay_score,
:current_season_aegis_score,
:previous_season_aegis_score
);"""

        INSERT_NEWS = """INSERT INTO squadrons_news_historical (
        operation_id, 
        type_of_news, 
        news_id, 
        date, 
        category, 
        activity, 
        season, 
        bookmark, 
        motd, 
        author, 
        cmdr_id, 
        user_id
        ) values (
        :operation_id,
        :type_of_news,
        :news_id,
        :date,
        :category,
        :activity,
        :season,
        :bookmark,
        :motd,
        :author,
        :cmdr_id,
        :user_id
        );"""

    class OLD:
        ALL_RECORDS = 'select * from squads_states order by inserted_timestamp;'
        NEWS_IN_TIME_BOUND = '''select * 
        from news 
        where squad_id = :squad_id and 
        inserted_timestamp between :low_bound and :high_bound and
        category = 'Squadrons_History_Category_PublicStatement' and
        "date" is not null and
        type_of_news = 'public_statements';'''
        ALL_NEWS_RECORDS = '''select * 
        from news
        where 
        category = 'Squadrons_History_Category_PublicStatement' and
        "date" is not null and
        type_of_news = 'public_statements';'''


exiting: bool = False


def exit_handler(_, __):
    global exiting
    exiting = True


signal.signal(signal.SIGINT, exiting)
signal.signal(signal.SIGTERM, exiting)


def allocate_operation_id(_squad_id: int, _timestamp: str) -> int:
    new_db.execute(QUERIES.NEW.CREATE_OPERATION_ID, {'squad_id': _squad_id, 'timestamp': _timestamp})
    return new_db.execute(QUERIES.NEW.GET_OPERATION_ID).fetchone()['operation_id']


new_db.executescript(QUERIES.NEW.SCHEMA)

news: dict[int, list[dict]] = defaultdict(list)
news_cache_timer = time()
for one_news in old_db.execute(QUERIES.OLD.ALL_NEWS_RECORDS):
    news[one_news['squad_id']].append(one_news)

print(f'news cached for {time() - news_cache_timer} s')

iterations_counter = 1
loop_timer = time()
loop_timer_secondary = time()

row: dict
for row in old_db.execute(QUERIES.OLD.ALL_RECORDS):
    if exiting:
        break

    squad_id: int = row['squad_id']
    # print(f'Processing: {squad_id}')
    timestamp: str = row['inserted_timestamp']
    if row['tag'] is None:
        # "Deleted" record for squad_id
        if new_db.execute(QUERIES.NEW.IS_DELETED, {'squad_id': squad_id}).fetchone()['deleted'] == 0:
            # with new_db:
            operation_id = allocate_operation_id(squad_id, timestamp)
            new_db.execute(QUERIES.NEW.INSERT_DELETED_SQUAD, {'operation_id': operation_id, 'squad_id': squad_id})

    else:
        # it's usual update/first update record
        # with new_db:
        operation_id = allocate_operation_id(squad_id, timestamp)
        row['operation_id'] = operation_id
        new_db.execute(
            QUERIES.NEW.INSERT_INFO,
            row
        )
        parsed_timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        delta = timedelta(minutes=1)
        low_bound = parsed_timestamp - delta
        high_bound = parsed_timestamp + delta

        for one_squad_news in news[squad_id]:
            if low_bound < datetime.strptime(one_squad_news['inserted_timestamp'], '%Y-%m-%d %H:%M:%S') < high_bound:
                one_squad_news['operation_id'] = operation_id
                new_db.execute(QUERIES.NEW.INSERT_NEWS, one_squad_news)
                break

    if iterations_counter % 1000 == 0:
        new_db.commit()
        print(f'Iterations: {iterations_counter}; avg iteration time: {(time() - loop_timer)/iterations_counter} s; avg local iter time {(time() - loop_timer_secondary)/1000} s')
        loop_timer_secondary = time()

    iterations_counter += 1

new_db.commit()
print(f'Iterations: {iterations_counter}; avg total iter time: {(time() - loop_timer)/iterations_counter} s')
