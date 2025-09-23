// path: vsc-no-code/nocode-studio-core/webview/src/components/Canvas.tsx
import React from 'react';

export default function Canvas() {
    return (
        <div className="canvas-root">
            <div className="canvas-left">
                <div className="toolbox">Components</div>
            </div>
            <div className="canvas-center">
                <div className="drop-zone">Drag components here</div>
            </div>
            <div className="canvas-right">
                <div className="properties">Properties</div>
            </div>
        </div>
    );
}
