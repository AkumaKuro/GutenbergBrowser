This project involves a small "Gutenberg API" that allows me to query through all books available in Gutenberg, by fetching every book title and book id through HTTP requests, and storing them in the GutenBerg.db file.

Note that I already updated the database before turning in the program, so making an update should not be required.

Simply start the program. It will prompt you whether you want to update the database first.

Type in any title you can think of. The program has a built-in similarity check that will find you the top 5 titles closest to your input, based on the Levenshtein distance algorithm.

By selecting the ID of the book from those top 5, you will receive a link to the book, and can start reading.

The program keeps track of your last book, and you can reopen the same book when restarting the program.

Just click on the link, and it will redirect you to the book you chose.