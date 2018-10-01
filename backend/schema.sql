CREATE TABLE IF NOT EXISTS posted_inktober(
    message_id BIGINT PRIMARY KEY,
    user_id BIGINT,
    time_added TIMESTAMP DEFAULT now()
)
