using CaptureScreenMcp;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using ModelContextProtocol.Server;
using System.Runtime.Versioning;

namespace CaptureScreenMcp;

[SupportedOSPlatform("windows")]
public static class Program
{
    public static async Task Main(string[] args)
    {
        var builder = Microsoft.Extensions.Hosting.Host.CreateApplicationBuilder(args);
        builder.Logging.ClearProviders();

        builder.Services
            .AddMcpServer()
            .WithStdioServerTransport()
            .WithTools<CaptureTools>();

        await builder.Build().RunAsync();
    }
}
