import { Route, Routes } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './routes/Home';
import BolsaFamilia from './routes/BolsaFamilia';
import Equipamentos from './routes/Equipamentos';
import Emendas from './routes/Emendas';
import UroPro from './routes/UroPro';
import UroProArticleStandalone from './routes/UroProArticleStandalone';
import NotFound from './routes/NotFound';

export default function App() {
  return (
    <Routes>
      {/* Standalone article views (no sidebar, full-page) — opened in new tab
          from the vertical pages. Pattern matches "PDF in new tab" UX of
          BolsaFamilia/Emendas, but for verticals with dynamically-generated
          HTML articles instead of static PDFs. */}
      <Route path="/incontinencia-urinaria/artigo" element={<UroProArticleStandalone />} />

      <Route element={<Layout />}>
        <Route path="/"                       element={<Home />} />
        <Route path="/bolsa-familia"          element={<BolsaFamilia />} />
        <Route path="/equipamentos"           element={<Equipamentos />} />
        <Route path="/emendas"                element={<Emendas />} />
        <Route path="/incontinencia-urinaria" element={<UroPro />} />
        <Route path="*"                       element={<NotFound />} />
      </Route>
    </Routes>
  );
}
