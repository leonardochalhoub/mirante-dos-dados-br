import { Route, Routes } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './routes/Home';
import BolsaFamilia from './routes/BolsaFamilia';
import SaudeMri from './routes/SaudeMri';
import Emendas from './routes/Emendas';
import NotFound from './routes/NotFound';

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/"               element={<Home />} />
        <Route path="/bolsa-familia"  element={<BolsaFamilia />} />
        <Route path="/saude-mri"      element={<SaudeMri />} />
        <Route path="/emendas"        element={<Emendas />} />
        <Route path="*"               element={<NotFound />} />
      </Route>
    </Routes>
  );
}
