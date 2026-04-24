import { Link } from 'react-router-dom';
import PageHeader from '../components/PageHeader';

export default function NotFound() {
  return (
    <>
      <PageHeader
        eyebrow="404"
        title="Página não encontrada"
        subtitle="A rota que você procurou não existe (ainda)."
        withFlag={false}
      />
      <p><Link to="/">Voltar pra página inicial</Link></p>
    </>
  );
}
