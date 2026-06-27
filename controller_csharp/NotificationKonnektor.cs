using System;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;

namespace HeroicCoreController {
    public class NotificationKonnektor {
        private static readonly HttpClient client = new HttpClient();
        private readonly string _webhookUrl = "DEIN_WEBHOOK_URL";

        public async Task SendAlert(string message) {
            string payload = $"{{\"content\": \"[HEROIC CORE ALERT] {message}\"}}";
            await client.PostAsync(_webhookUrl, new StringContent(payload, Encoding.UTF8, "application/json"));
        }
    }
}
