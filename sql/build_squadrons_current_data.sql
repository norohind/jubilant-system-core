BEGIN;
delete from squadrons_current_data;
insert into squadrons_current_data
select
       squad_id,
       name,
       tag,
       owner_id,
       owner_name,
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
       delete_after,
       credits_balance,
       credits_in,
       credits_out,
       user_tags,
       member_count,
       online_count,
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
       previous_season_aegis_score,
       motd,
       author,
       cmdr_id,
       user_id,
       news_id,
       "date",
       squadrons_historical_data.operation_id as operation_id,
       max(timestamp) as updated
from squadrons_historical_data
    inner join operations_info oi
        on oi.operation_id = squadrons_historical_data.operation_id
    left join squadrons_news_historical snh
        on oi.operation_id = snh.operation_id
where squad_id not in (select squad_id from squadrons_deleted)
group by squad_id;
COMMIT;