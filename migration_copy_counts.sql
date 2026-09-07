USE dblib;

ALTER TABLE books ADD COLUMN total_copies INT UNSIGNED NOT NULL DEFAULT 1 AFTER publication_year;
ALTER TABLE books ADD COLUMN available_copies INT UNSIGNED NOT NULL DEFAULT 1 AFTER total_copies;

-- Existing borrowed/overdue transactions represent unavailable copies.
UPDATE books b
SET b.available_copies = GREATEST(0, b.total_copies - (
    SELECT COUNT(*) FROM book_transactions t
    WHERE t.book_id = b.id AND t.status IN ('borrowed', 'overdue', 'lost')
));
UPDATE books SET status = CASE WHEN available_copies = 0 THEN 'borrowed' ELSE status END;
