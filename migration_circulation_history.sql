USE dblib;

ALTER TABLE users
    ADD COLUMN username_changed_at DATETIME NULL,
    ADD COLUMN password_changed_at DATETIME NULL;

ALTER TABLE book_transactions
    MODIFY COLUMN status ENUM('borrowed', 'renewed', 'returned', 'overdue', 'lost') NOT NULL DEFAULT 'borrowed';

CREATE TABLE IF NOT EXISTS borrow_transaction_events (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    transaction_id BIGINT UNSIGNED NULL,
    request_id BIGINT UNSIGNED NOT NULL,
    action ENUM('approved', 'declined', 'renewed', 'returned') NOT NULL,
    actor_id BIGINT UNSIGNED NOT NULL,
    acted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_transaction_event_transaction FOREIGN KEY (transaction_id) REFERENCES book_transactions(id) ON DELETE CASCADE,
    CONSTRAINT fk_transaction_event_request FOREIGN KEY (request_id) REFERENCES borrow_requests(id) ON DELETE CASCADE,
    CONSTRAINT fk_transaction_event_actor FOREIGN KEY (actor_id) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_transaction_events_transaction (transaction_id, action),
    INDEX idx_transaction_events_request (request_id, action)
) ENGINE=InnoDB;