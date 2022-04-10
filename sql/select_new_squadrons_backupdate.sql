select * from
              (
                  select distinct squad_id
                  from squadrons_historical_data
                      inner join operations_info oi
                          on oi.operation_id = squadrons_historical_data.operation_id
                  except select squad_id from squadrons_deleted
                  )
order by squad_id desc
limit :count;