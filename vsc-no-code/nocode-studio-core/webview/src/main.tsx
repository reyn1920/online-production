// path: vsc-no-code/nocode-studio-core/webview/src/main.tsx
import React from 'react';
import { createRoot } from 'react-dom/client';
import Canvas from './components/Canvas';
import './styles.css';

function App() {
    return (
        <div className="nocode-root">
            <header className="studio-header">No-Code Studio Runtime</header>
            <Canvas />
        </div>
    );
}

const container = document.getElementById('root')!;
const root = createRoot(container);
root.render(<App />);
