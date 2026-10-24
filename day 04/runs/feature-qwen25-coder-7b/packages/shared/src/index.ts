export type Book = {
  id: string;
  title: string;
  authors: string[];
  createdAt: number;
};

export type BookDetail = Book & {
  spine: string[];
};

export type ReadingProgress = {
  bookId: string;
  spineIndex: number;
  scrollRatio: number;
  updatedAt: number;
};

export type Chapter = {
  index: number;
  href: string;
  html: string;
};
