CREATE DATABASE IF NOT EXISTS dblib CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE dblib;

CREATE TABLE IF NOT EXISTS users (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(160) NOT NULL,
    email VARCHAR(255) UNIQUE,
    role ENUM('admin', 'staff', 'member') NOT NULL,
    status ENUM('active', 'suspended') NOT NULL DEFAULT 'active',
    approved_by BIGINT UNSIGNED NULL,
    approved_at DATETIME NULL,
    username_changed_at DATETIME NULL,
    password_changed_at DATETIME NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_users_approver FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS members (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL UNIQUE,
    membership_no VARCHAR(30) NOT NULL UNIQUE,
    phone VARCHAR(40),
    address VARCHAR(255),
    status ENUM('active', 'suspended') NOT NULL DEFAULT 'active',
    joined_at DATE NOT NULL,
    CONSTRAINT fk_members_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS publishers (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(180) NOT NULL UNIQUE,
    email VARCHAR(255),
    phone VARCHAR(40),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS authors (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(180) NOT NULL,
    biography TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS bookshelves (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(40) NOT NULL UNIQUE,
    section VARCHAR(120) NOT NULL,
    description VARCHAR(255)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS books (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    isbn VARCHAR(20) NOT NULL UNIQUE,
    author_id BIGINT UNSIGNED NULL,
    publisher_id BIGINT UNSIGNED NULL,
    shelf_id BIGINT UNSIGNED NULL,
    publication_year SMALLINT UNSIGNED,
    total_copies INT UNSIGNED NOT NULL DEFAULT 1,
    available_copies INT UNSIGNED NOT NULL DEFAULT 1,
    status ENUM('available', 'reserved', 'borrowed') NOT NULL DEFAULT 'available',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_books_author FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE SET NULL,
    CONSTRAINT fk_books_publisher FOREIGN KEY (publisher_id) REFERENCES publishers(id) ON DELETE SET NULL,
    CONSTRAINT fk_books_shelf FOREIGN KEY (shelf_id) REFERENCES bookshelves(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS borrow_requests (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    member_id BIGINT UNSIGNED NOT NULL,
    book_id BIGINT UNSIGNED NOT NULL,
    request_type ENUM('borrow', 'reserve') NOT NULL,
    status ENUM('pending', 'approved', 'declined', 'cancelled') NOT NULL DEFAULT 'pending',
    note VARCHAR(500),
    requested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reviewed_by BIGINT UNSIGNED NULL,
    reviewed_at DATETIME NULL,
    CONSTRAINT fk_requests_member FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE,
    CONSTRAINT fk_requests_book FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
    CONSTRAINT fk_requests_reviewer FOREIGN KEY (reviewed_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_requests_status (status)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS book_transactions (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    request_id BIGINT UNSIGNED NULL,
    book_id BIGINT UNSIGNED NOT NULL,
    member_id BIGINT UNSIGNED NOT NULL,
    issued_by BIGINT UNSIGNED NOT NULL,
    returned_to BIGINT UNSIGNED NULL,
    issue_date DATE NOT NULL,
    due_date DATE NOT NULL,
    return_date DATE NULL,
    renewal_count TINYINT UNSIGNED NOT NULL DEFAULT 0,
    fine_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    status ENUM('borrowed', 'renewed', 'returned', 'overdue') NOT NULL DEFAULT 'borrowed',
    CONSTRAINT fk_transactions_request FOREIGN KEY (request_id) REFERENCES borrow_requests(id) ON DELETE SET NULL,
    CONSTRAINT fk_transactions_book FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE RESTRICT,
    CONSTRAINT fk_transactions_member FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE RESTRICT,
    CONSTRAINT fk_transactions_issuer FOREIGN KEY (issued_by) REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT fk_transactions_returner FOREIGN KEY (returned_to) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_transactions_member_status (member_id, status),
    INDEX idx_transactions_due_date (due_date)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    actor_id BIGINT UNSIGNED NULL,
    action VARCHAR(40) NOT NULL,
    entity_type VARCHAR(60) NOT NULL,
    entity_id BIGINT UNSIGNED NULL,
    details JSON NULL,
    ip_address VARCHAR(45),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_audit_actor FOREIGN KEY (actor_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_audit_entity (entity_type, entity_id),
    INDEX idx_audit_created (created_at)
) ENGINE=InnoDB;

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
