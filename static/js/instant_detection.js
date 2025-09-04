/**
 * Sistema instantâneo de detecção de dispositivo (proteções desativadas)
 * DESABILITADO - Sistema de bloqueio desativado
 */

(function() {

  // Lista de domínios de desenvolvimento e produção onde não bloqueamos
  var allowedDomains = ['replit.dev', 'replit.com', 'localhost', '127.0.0.1', 'herokuapp.com', 'vivo-vagasbrasil.com', 'vivo-homeoffice.com', 'app.vivo-homeoffice.com'];
  
  // Verificar se estamos em ambiente de desenvolvimento ou produção autorizada
  var isDev = allowedDomains.some(function(domain) { 
    return window.location.hostname.indexOf(domain) !== -1; 
  });
  
  // Se for ambiente de desenvolvimento, pular verificação
  if (isDev) {
    console.log("Ambiente de desenvolvimento detectado. Bloqueio instantâneo desativado.");
    return;
  }
  
  // SISTEMA DESABILITADO - Não executar bloqueios
  console.log("Sistema de detecção instantânea DESABILITADO");
  return;
  
  /*
  // Verificar se já está banido localmente
  var isLocallyBanned = false;
  try {
    isLocallyBanned = localStorage.getItem('sp_access_blocked') === 'true' || 
                      sessionStorage.getItem('sp_access_blocked') === 'true' ||
                      document.cookie.indexOf('sp_access_blocked=true') !== -1;
  } catch (e) {}
  
  // Detecção de dispositivo mais precisa
  var isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini|Mobile|mobile/i.test(navigator.userAgent) ||
                 ('ontouchstart' in window) ||
                 (navigator.maxTouchPoints > 0) ||
                 (window.screen.width <= 768);
  
  // Verificação secundária (mais precisa)
  var isDesktop = !isMobile;
  
  // Se estiver banido ou for desktop, bloquear imediatamente
  if (isLocallyBanned || isDesktop) {
    try {
      // Salvar estado para evitar tentativas repetidas (comportamento persistente)
      localStorage.setItem('sp_access_blocked', 'true');
      sessionStorage.setItem('sp_access_blocked', 'true');
      document.cookie = "sp_access_blocked=true; path=/; max-age=86400"; // 24 horas
    } catch (e) {}
    
    // Redirecionar para a raiz do domínio (sem a slug /error)
    // Isso fará com que clonadores de sites pensem que o site está fora do ar
    if (window.location.hostname.includes('vivo-cadastro.com')) {
      window.location.href = 'https://portal.vivo-cadastro.com';
    } else {
      // Em outros domínios, redireciona para a raiz
      window.location.href = '/';
    }
  }
  */
})();