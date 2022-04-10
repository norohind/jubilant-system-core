insert into settings (
                      key, int_value
                      ) values (
                                :key,
                                :int_value
                                ) on conflict do update set int_value = :int_value where key = :key;