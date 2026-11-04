// BookShelf fixture site (GATP T-003). Plain JS, state in localStorage.
// Behaviors are documented in fixtures/README.md (FX-1 … FX-6).
'use strict';

const USER_KEY = 'bookshelf.user';
const BOOKS_KEY = 'bookshelf.books';
const NOTICE_KEY = 'bookshelf.notice';
const VALID_USER = { username: 'tester', password: 'secret123' };
const GENRES = ['Fiction', 'Science', 'History', 'Children'];
const SEED_BOOKS = [
  { title: 'The Left Hand of Darkness', author: 'Ursula K. Le Guin', year: 1969, genre: 'Fiction', draft: false },
  { title: 'A Brief History of Time', author: 'Stephen Hawking', year: 1988, genre: 'Science', draft: false },
  { title: 'The Guns of August', author: 'Barbara W. Tuchman', year: 1962, genre: 'History', draft: false },
  { title: 'Matilda', author: 'Roald Dahl', year: 1988, genre: 'Children', draft: false },
  { title: 'Kindred', author: 'Octavia E. Butler', year: 1979, genre: 'Fiction', draft: false },
];

function loadBooks() {
  const raw = localStorage.getItem(BOOKS_KEY);
  return raw ? JSON.parse(raw) : SEED_BOOKS.slice();
}

function saveBooks(books) {
  localStorage.setItem(BOOKS_KEY, JSON.stringify(books));
}

function requireLogin() {
  if (!localStorage.getItem(USER_KEY)) {
    window.location.href = 'index.html';
    return false;
  }
  return true;
}

function logout() {
  localStorage.removeItem(USER_KEY);
  window.location.href = 'index.html';
}

// FX-1 / FX-2: login
function initLogin() {
  const form = document.getElementById('login-form');
  const error = document.getElementById('login-error');
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    const username = form.username.value.trim();
    const password = form.password.value;
    if (username === VALID_USER.username && password === VALID_USER.password) {
      localStorage.setItem(USER_KEY, username);
      window.location.href = 'books.html';
    } else {
      error.textContent = 'Invalid username or password.';
    }
  });
}

// FX-3 / FX-4: list, search and genre filter
function initList() {
  if (!requireLogin()) return;
  document.getElementById('current-user').textContent = localStorage.getItem(USER_KEY);
  const notice = localStorage.getItem(NOTICE_KEY);
  if (notice) {
    const box = document.getElementById('notice');
    box.textContent = notice;
    box.hidden = false;
    localStorage.removeItem(NOTICE_KEY);
  }
  const search = document.getElementById('search');
  const genre = document.getElementById('genre-filter');
  const render = () => renderBooks(search.value.trim().toLowerCase(), genre.value);
  search.addEventListener('input', render);
  genre.addEventListener('change', render);
  render();
}

function renderBooks(query, genre) {
  const body = document.getElementById('book-rows');
  const books = loadBooks().filter(
    (b) =>
      (query === '' || b.title.toLowerCase().includes(query) || b.author.toLowerCase().includes(query)) &&
      (genre === '' || b.genre === genre),
  );
  body.innerHTML = '';
  for (const b of books) {
    const row = document.createElement('tr');
    const title = document.createElement('td');
    title.textContent = b.title;
    if (b.draft) {
      const badge = document.createElement('span');
      badge.className = 'badge';
      badge.textContent = 'Draft';
      title.appendChild(badge);
    }
    row.appendChild(title);
    for (const value of [b.author, String(b.year), b.genre]) {
      const cell = document.createElement('td');
      cell.textContent = value;
      row.appendChild(cell);
    }
    body.appendChild(row);
  }
  document.getElementById('result-count').textContent = `${books.length} book(s)`;
  document.getElementById('empty-state').hidden = books.length !== 0;
}

// FX-5 / FX-6: add-book form with validation
function validateBook(form) {
  const errors = {};
  const title = form.title.value.trim();
  const author = form.author.value.trim();
  const yearText = form.year.value.trim();
  const year = Number(yearText);
  const thisYear = new Date().getFullYear();
  if (title === '') errors.title = 'Title is required.';
  if (author === '') errors.author = 'Author is required.';
  if (yearText === '' || !Number.isInteger(year) || year < 1450 || year > thisYear) {
    errors.year = `Year must be a whole number between 1450 and ${thisYear}.`;
  }
  if (!GENRES.includes(form.genre.value)) errors.genre = 'Choose a genre.';
  return { errors, book: { title, author, year, genre: form.genre.value } };
}

function showErrors(errors) {
  for (const field of ['title', 'author', 'year', 'genre']) {
    document.getElementById(`${field}-error`).textContent = errors[field] || '';
  }
}

function initAdd() {
  if (!requireLogin()) return;
  const form = document.getElementById('book-form');
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    const draft = event.submitter && event.submitter.dataset.draft === 'true';
    const { errors, book } = validateBook(form);
    showErrors(errors);
    if (Object.keys(errors).length > 0) return;
    const books = loadBooks();
    books.push({ ...book, draft });
    saveBooks(books);
    localStorage.setItem(NOTICE_KEY, draft ? `Draft "${book.title}" saved.` : `Book "${book.title}" saved.`);
    window.location.href = 'books.html';
  });
}
