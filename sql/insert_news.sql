insert into squadrons_news_historical (
    operation_id,
    type_of_news,
    news_id,
    "date",
    category,
    motd,
    author,
    cmdr_id,
    user_id
) values
(
    :operation_id,
    :type_of_news,
    :news_id,
    :date,
    :category,
    :motd,
    :author,
    :cmdr_id,
    :user_id
);