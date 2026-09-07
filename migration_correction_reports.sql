USE dblib;

CREATE TABLE IF NOT EXISTS catalogue_correction_reports (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    submitted_by BIGINT UNSIGNED NOT NULL,
    entity_type ENUM('book', 'author', 'publisher', 'bookshelf') NOT NULL,
    entity_id BIGINT UNSIGNED NULL,
    reason VARCHAR(1000) NOT NULL,
    requested_action ENUM('correction', 'deletion') NOT NULL,
    status ENUM('pending', 'resolved', 'declined') NOT NULL DEFAULT 'pending',
    submitted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    handled_by BIGINT UNSIGNED NULL,
    handled_at DATETIME NULL,
    CONSTRAINT fk_correction_submitted_by FOREIGN KEY (submitted_by) REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT fk_correction_handled_by FOREIGN KEY (handled_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_correction_status (status),
    INDEX idx_correction_entity (entity_type, entity_id)
) ENGINE=InnoDB;
