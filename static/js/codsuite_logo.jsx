function CodsuiteLogo() {
    // Stylized card logo for COD$uite — rounded card with border gradient and inner shadow
    return (
        <div style={{display: 'flex', justifyContent: 'center', alignItems: 'center', width: '100%'}}>
            <svg width="130" height="130" viewBox="0 0 130 130" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Logo COD$uite" preserveAspectRatio="xMidYMid meet">
                <defs>
                    <linearGradient id="borderGrad" x1="0" y1="0" x2="1" y2="1">
                        <stop offset="0%" stopColor="#6b7280" stopOpacity="0.18" />
                        <stop offset="50%" stopColor="#111827" stopOpacity="0.28" />
                        <stop offset="100%" stopColor="#000000" stopOpacity="0.35" />
                    </linearGradient>
                    <linearGradient id="innerGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#0b1220" />
                        <stop offset="100%" stopColor="#111827" />
                    </linearGradient>
                    <filter id="innerShadow" x="-50%" y="-50%" width="200%" height="200%">
                        <feOffset dx="0" dy="6" result="offOut"/>
                        <feGaussianBlur in="offOut" stdDeviation="8" result="blurOut"/>
                        <feComposite in="blurOut" in2="SourceAlpha" operator="out" result="comp"/>
                        <feColorMatrix type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 0.45 0"/>
                    </filter>
                </defs>

                {/* outer border */}
                <rect x="0" y="0" rx="18" width="130" height="130" fill="url(#borderGrad)" />

                {/* inner card (slightly inset) */}
                <rect x="8" y="8" rx="14" width="114" height="114" fill="url(#innerGrad)" filter="url(#innerShadow)" />

                {/* glass highlight */}
                <rect x="10" y="10" rx="12" width="110" height="56" fill="rgba(255,255,255,0.03)" />

                {/* logo text - single line, smaller to fit reduced card */}
                <g transform="translate(0,0)">
                    <text x="65" y="72" textAnchor="middle" fontFamily="Arial, Helvetica, sans-serif" fontSize="22" fontWeight="800" fill="#ffffff" dominantBaseline="middle">COD$uite</text>
                </g>
            </svg>
        </div>
    );
}

const container = document.getElementById('codsuite-logo');
if (container) {
    try {
        const root = ReactDOM.createRoot(container);
        root.render(<CodsuiteLogo />);
    } catch (e) {
        // Fallback for older React versions or environments
        ReactDOM.render(React.createElement(CodsuiteLogo), container);
    }
}
