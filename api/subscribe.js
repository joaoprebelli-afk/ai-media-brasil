// api/subscribe.js — Vercel Serverless Function
// Recebe POST { email, utm_source, utm_medium } e chama a API do Beehiiv server-side.
// A API key fica em variável de ambiente BEEHIIV_API_KEY (nunca exposta no frontend).

const PUB_ID = 'pub_b9616b61-1027-40e4-8884-6e1d0b127ae7';

export default async function handler(req, res) {
  // Apenas POST
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { email, utm_source, utm_medium } = req.body || {};

  // Validação básica de email
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return res.status(400).json({ error: 'Email inválido' });
  }

  const API_KEY = process.env.BEEHIIV_API_KEY;
  if (!API_KEY) {
    console.error('BEEHIIV_API_KEY não configurada');
    return res.status(500).json({ error: 'Configuração incompleta no servidor' });
  }

  try {
    const response = await fetch(
      `https://api.beehiiv.com/v2/publications/${PUB_ID}/subscriptions`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${API_KEY}`,
        },
        body: JSON.stringify({
          email,
          utm_source: utm_source || 'website',
          utm_medium: utm_medium || 'organic',
          referring_site: 'joaogpt.com',
          send_welcome_email: true,
          reactivate_existing: false,
        }),
      }
    );

    const data = await response.json();

    if (!response.ok) {
      console.error('Beehiiv API error:', response.status, data);
      return res.status(response.status).json({ error: data });
    }

    return res.status(200).json({ success: true });
  } catch (err) {
    console.error('Beehiiv subscribe error:', err);
    return res.status(500).json({ error: 'Erro interno do servidor' });
  }
}
