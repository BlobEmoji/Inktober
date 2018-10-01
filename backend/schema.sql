CREATE TABLE IF NOT EXISTS posted_inktober(
    message_id BIGINT PRIMARY KEY,
    user_id BIGINT,
    message TEXT,
    time_added TIMESTAMP DEFAULT now()
)
