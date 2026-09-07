USE dblib;


INSERT IGNORE INTO users (id, username, password_hash, full_name, email, role, status, approved_by, approved_at) VALUES
(1, 'admin.demo', 'scrypt:32768:8:1$9AyVMf7cIxGWfFg7$201cec27a812b2bfeb1651d103c2d440a777f978a15d01a333235bd4beb922ad23744ac9acb6ed85b9a74c39e3f971778e864cd0a531d13b361f6ec9f517a7e5', 'Amina Okafor', 'amina.admin@example.com', 'admin', 'active', NULL, NULL),
(2, 'staff.demo', 'scrypt:32768:8:1$9AyVMf7cIxGWfFg7$201cec27a812b2bfeb1651d103c2d440a777f978a15d01a333235bd4beb922ad23744ac9acb6ed85b9a74c39e3f971778e864cd0a531d13b361f6ec9f517a7e5', 'Jon Bell', 'jon.staff@example.com', 'staff', 'active', 1, NOW()),
(3, 'maya.chen', 'scrypt:32768:8:1$9AyVMf7cIxGWfFg7$201cec27a812b2bfeb1651d103c2d440a777f978a15d01a333235bd4beb922ad23744ac9acb6ed85b9a74c39e3f971778e864cd0a531d13b361f6ec9f517a7e5', 'Maya Chen', 'maya.chen@example.com', 'member', 'active', 1, NOW()),
(4, 'noah.williams', 'scrypt:32768:8:1$9AyVMf7cIxGWfFg7$201cec27a812b2bfeb1651d103c2d440a777f978a15d01a333235bd4beb922ad23744ac9acb6ed85b9a74c39e3f971778e864cd0a531d13b361f6ec9f517a7e5', 'Noah Williams', 'noah.williams@example.com', 'member', 'active', 1, NOW()),
(5, 'sofia.reyes', 'scrypt:32768:8:1$9AyVMf7cIxGWfFg7$201cec27a812b2bfeb1651d103c2d440a777f978a15d01a333235bd4beb922ad23744ac9acb6ed85b9a74c39e3f971778e864cd0a531d13b361f6ec9f517a7e5', 'Sofia Reyes', 'sofia.reyes@example.com', 'member', 'active', 1, NOW()),
(6, 'liam.patel', 'scrypt:32768:8:1$9AyVMf7cIxGWfFg7$201cec27a812b2bfeb1651d103c2d440a777f978a15d01a333235bd4beb922ad23744ac9acb6ed85b9a74c39e3f971778e864cd0a531d13b361f6ec9f517a7e5', 'Liam Patel', 'liam.patel@example.com', 'member', 'active', 1, NOW());

INSERT IGNORE INTO members (id, user_id, membership_no, phone, address, status, joined_at) VALUES
(1, 3, 'LIB-1001', '555-0101', '14 Cedar Street', 'active', '2025-01-12'),
(2, 4, 'LIB-1002', '555-0102', '29 River Road', 'active', '2025-02-03'),
(3, 5, 'LIB-1003', '555-0103', '7 Market Lane', 'active', '2025-03-18'),
(4, 6, 'LIB-1004', '555-0104', '81 Garden Avenue', 'active', '2025-04-22');

INSERT IGNORE INTO publishers (id, name, email, phone) VALUES
(1, 'North Star Press', 'hello@northstar.example', '555-1001'),
(2, 'Riverbend Books', 'contact@riverbend.example', '555-1002'),
(3, 'Cedar House Publishing', 'info@cedarhouse.example', '555-1003'),
(4, 'Open Field Editions', 'hello@openfield.example', '555-1004'),
(5, 'Lantern Works', 'press@lanternworks.example', '555-1005');

INSERT IGNORE INTO authors (id, name, biography) VALUES
(1, 'Nia Harper', 'Novelist and essayist focused on community and belonging.'),
(2, 'Elias Morgan', 'Writer of practical guides about history and civic life.'),
(3, 'Priya Shah', 'Author of contemporary fiction and short stories.'),
(4, 'Daniel Brooks', 'Children''s author and literacy advocate.'),
(5, 'Ruth Alvarez', 'Poet and translator.'),
(6, 'Marcus Green', 'Science writer and educator.'),
(7, 'Helen Ito', 'Illustrator and graphic storyteller.'),
(8, 'Samuel Okoro', 'Historian of cities and public spaces.');

INSERT IGNORE INTO bookshelves (id, code, section, description) VALUES
(1, 'A-01', 'Fiction', 'Contemporary fiction and novels'),
(2, 'A-02', 'Fiction', 'Classic fiction and literature'),
(3, 'B-01', 'History', 'History, geography, and society'),
(4, 'C-01', 'Children', 'Early readers and children''s books'),
(5, 'D-01', 'Science', 'Science, technology, and nature');

INSERT IGNORE INTO books (id, title, isbn, author_id, publisher_id, shelf_id, publication_year, total_copies, available_copies, status) VALUES
(1, 'The Map of Small Things', '9780000000001', 1, 1, 1, 2022, 3, 3, 'available'),
(2, 'A City Built Together', '9780000000002', 2, 2, 3, 2021, 2, 1, 'available'),
(3, 'The Paper Garden', '9780000000003', 3, 3, 1, 2020, 2, 2, 'available'),
(4, 'Questions for Tomorrow', '9780000000004', 6, 4, 5, 2024, 1, 1, 'available'),
(5, 'The Moonlit Library', '9780000000005', 4, 5, 4, 2019, 2, 2, 'reserved'),
(6, 'Letters from the River', '9780000000006', 5, 1, 2, 2023, 4, 4, 'available'),
(7, 'How Neighborhoods Grow', '9780000000007', 8, 2, 3, 2022, 2, 2, 'available'),
(8, 'The Brightest Kite', '9780000000008', 4, 3, 4, 2018, 3, 3, 'available'),
(9, 'Everyday Astronomy', '9780000000009', 6, 4, 5, 2023, 2, 1, 'available'),
(10, 'Stories We Carry', '9780000000010', 1, 5, 2, 2021, 2, 2, 'available');

INSERT IGNORE INTO borrow_requests (id, member_id, book_id, request_type, status, note, requested_at, reviewed_by, reviewed_at) VALUES
(1, 1, 2, 'borrow', 'approved', 'Needed for a local history project.', '2026-08-20 10:15:00', 2, '2026-08-20 11:00:00'),
(2, 2, 5, 'reserve', 'pending', 'Please hold this for the weekend.', '2026-09-01 09:30:00', NULL, NULL),
(3, 3, 9, 'borrow', 'approved', NULL, '2026-08-18 14:20:00', 2, '2026-08-18 15:00:00'),
(4, 4, 1, 'borrow', 'pending', NULL, '2026-09-02 16:45:00', NULL, NULL),
(5, 1, 3, 'reserve', 'declined', 'Requested while another reservation was active.', '2026-08-12 12:05:00', 2, '2026-08-12 13:10:00'),
(6, 2, 7, 'borrow', 'cancelled', NULL, '2026-08-10 08:45:00', NULL, NULL);

INSERT IGNORE INTO book_transactions (id, request_id, book_id, member_id, issued_by, issue_date, due_date, return_date, renewal_count, fine_amount, status) VALUES
(1, 1, 2, 1, 2, '2026-08-20', '2026-09-03', NULL, 0, 0.00, 'overdue'),
(2, 3, 9, 3, 2, '2026-08-18', '2026-09-01', NULL, 1, 2.50, 'overdue'),
(3, NULL, 6, 2, 2, '2026-07-01', '2026-07-15', '2026-07-12', 0, 0.00, 'returned'),
(4, NULL, 8, 4, 2, '2026-06-05', '2026-06-19', '2026-06-18', 0, 0.00, 'returned');

INSERT INTO audit_logs (actor_id, action, entity_type, entity_id, details, ip_address) VALUES
(1, 'create', 'user', 2, JSON_OBJECT('role', 'staff'), '127.0.0.1'),
(1, 'approve', 'user', 2, JSON_OBJECT('status', 'active'), '127.0.0.1'),
(2, 'create', 'book', 1, JSON_OBJECT('title', 'The Map of Small Things'), '127.0.0.1'),
(2, 'create', 'book', 2, JSON_OBJECT('title', 'A City Built Together'), '127.0.0.1'),
(2, 'approve', 'borrow_request', 1, JSON_OBJECT('book_id', 2), '127.0.0.1'),
(2, 'approve', 'borrow_request', 3, JSON_OBJECT('book_id', 9), '127.0.0.1'),
(2, 'decline', 'borrow_request', 5, JSON_OBJECT('reason', 'Existing reservation'), '127.0.0.1'),
(1, 'create', 'member', 1, JSON_OBJECT('membership_no', 'LIB-1001'), '127.0.0.1');

-- Quick verification: this returns the row counts loaded per table.
SELECT 'users' AS table_name, COUNT(*) AS row_count FROM users
UNION ALL SELECT 'members', COUNT(*) FROM members
UNION ALL SELECT 'publishers', COUNT(*) FROM publishers
UNION ALL SELECT 'authors', COUNT(*) FROM authors
UNION ALL SELECT 'bookshelves', COUNT(*) FROM bookshelves
UNION ALL SELECT 'books', COUNT(*) FROM books
UNION ALL SELECT 'borrow_requests', COUNT(*) FROM borrow_requests
UNION ALL SELECT 'book_transactions', COUNT(*) FROM book_transactions
UNION ALL SELECT 'audit_logs', COUNT(*) FROM audit_logs;
