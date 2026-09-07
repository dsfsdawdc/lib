USE dblib;

-- Run this once if dblib was created from the previous schema.sql.
ALTER TABLE books ADD COLUMN author_id BIGINT UNSIGNED NULL AFTER isbn;
ALTER TABLE books ADD CONSTRAINT fk_books_author FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE SET NULL;

-- Preserve the first author for each book, then remove the old join table.
UPDATE books b
JOIN (
    SELECT book_id, MIN(author_id) AS author_id
    FROM book_authors
    GROUP BY book_id
) ba ON ba.book_id = b.id
SET b.author_id = ba.author_id;

DROP TABLE book_authors;
