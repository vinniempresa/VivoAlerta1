/**
 * Sistema de detecção de dispositivos (proteções desativadas)
 */

// Função para detectar o tipo de dispositivo (sempre retorna autorizado)
function detectDevice() {
    return {
        isMobile: true,
        isTablet: false,
        isDesktop: false,
        isTouchDevice: true,
        isPortrait: true,
        screenWidth: window.innerWidth,
        screenHeight: window.innerHeight,
        userAgent: navigator.userAgent
    };
}

// Verificar se as ferramentas de desenvolvedor estão abertas (sempre retorna false)
function detectDevTools() {
    return false;
}

// Executar verificações e enviar resultados para o servidor
function sendDeviceInfo() {
    const deviceInfo = detectDevice();
    
    // Combinar todas as informações
    const data = {
        ...deviceInfo,
        devToolsOpen: false,
        timestamp: new Date().toISOString(),
        referrer: document.referrer,
        windowSize: {
            innerWidth: window.innerWidth,
            innerHeight: window.innerHeight,
            outerWidth: window.outerWidth,
            outerHeight: window.outerHeight
        }
    };
    
    // Enviar dados para o servidor usando fetch
    fetch('/check-device', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        // Sempre autorizar o acesso
        console.log("Acesso autorizado");
    })
    .catch(error => {
        console.log("Erro na verificação, mas acesso permitido");
    });
}

// Iniciar verificação
sendDeviceInfo();