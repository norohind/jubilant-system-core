"""
Workflow to discover new squadrons (db operations):
1. Get next id
2. Query info endpoint
3. If squadron exists:
    Insert squad_id into operations_info
    get operation_id
    Insert into squadrons_historical_data data from info endpoint
    Insert into squadrons_news_historical data from news endpoint

else:
    ignore, don't insert squad_id to squadrons_deleted

Workflow to update existing squadron:
1. Get most early updated squad from squadrons_current_data
2. Insert squad_id into operations_info
3. Get operation_id
4. Request info endpoint
    if squad exists:
        query news endpoint
        insert data from info and news queries to appropriate historical tables

    else:
        insert squad_id, operations_id to squadrons_deleted
"""