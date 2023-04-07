import { createRoot } from 'react-dom/client';
import App from './App';

document.addEventListener('DOMContentLoaded', async () => {
	const root = createRoot(document.getElementById('main'));
	root.render(<App />);
})
