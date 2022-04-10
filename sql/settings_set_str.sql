insert into settings (
                      key, txt_value
                      ) values (
                                :key,
                                :txt_value
                                ) on conflict do update set txt_value = :txt_value where key = :key;