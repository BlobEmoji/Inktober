CREATE TABLE IF NOT EXISTS posted_inktober(
    message_id BIGINT PRIMARY KEY,
    user_id BIGINT,
    message TEXT,
    inktober_day TEXT,
    time_added TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS my_posts_to_original (
    original_id BIGINT PRIMARY KEY,
    my_message_id BIGINT,
    my_channel_id BIGINT
);

CREATE TABLE IF NOT EXISTS my_message_to_original (
    my_message_id BIGINT PRIMARY KEY,
    original_id BIGINT,
    my_channel_id BIGINT
);
