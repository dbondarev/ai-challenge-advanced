import { BrowserRouter, Route, Routes } from "react-router-dom";
import { LibraryPage } from "./pages/LibraryPage.js";
import { ReaderPage } from "./pages/ReaderPage.js";

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LibraryPage />} />
        <Route path="/books/:id" element={<ReaderPage />} />
      </Routes>
    </BrowserRouter>
  );
}
