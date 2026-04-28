import { Route, Routes } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './routes/Home';
import BolsaFamilia from './routes/BolsaFamilia';
import Equipamentos from './routes/Equipamentos';
import Emendas from './routes/Emendas';
import UroPro from './routes/UroPro';
import Rais from './routes/Rais';
import FinOps from './routes/FinOps';
import NotFound from './routes/NotFound';

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/"                            element={<Home />} />
        <Route path="/bolsa-familia"               element={<BolsaFamilia />} />
        <Route path="/equipamentos"                element={<Equipamentos />} />
        <Route path="/emendas"                     element={<Emendas />} />
        <Route path="/incontinencia-urinaria"      element={<UroPro />} />
        <Route path="/rais"                        element={<Rais />} />
        <Route path="/finops"                      element={<FinOps />} />
        <Route path="*"                            element={<NotFound />} />
      </Route>
    </Routes>
  );
}
