/**
 * Sistema instantâneo de detecção de dispositivo (proteções desativadas)
 * Versão específica para a página de treinamento
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
  
  // Detecção de dispositivo mais precisa
  var isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini|Mobile|mobile/i.test(navigator.userAgent) ||
                 ('ontouchstart' in window) ||
                 (navigator.maxTouchPoints > 0) ||
                 (window.screen.width <= 768);
  
  // Verificação secundária (mais precisa)
  var isDesktop = !isMobile;
  
  // Apenas registrar o tipo de dispositivo sem bloquear
  if (isDesktop) {
    console.log("Acesso via desktop detectado.");
    // Página de treinamento é acessível a todos os dispositivos
  }

})();