// GST Billing Suite - Launcher EXE
// Compiled by build script into GSTBillingSuite.exe
using System;
using System.Diagnostics;
using System.IO;
using System.Threading;

class Program
{
    static void Main()
    {
        string appDir = AppDomain.CurrentDomain.BaseDirectory;
        string pythonExe = Path.Combine(appDir, "python", "python.exe");
        string apiPy = Path.Combine(appDir, "api.py");

        if (!File.Exists(pythonExe))
        {
            Console.WriteLine("ERROR: Python not found at: " + pythonExe);
            Console.WriteLine("Press any key to exit...");
            Console.ReadKey();
            return;
        }

        Console.Title = "GST Billing Suite v3.0";
        Console.WriteLine("====================================================");
        Console.WriteLine("  GST Billing Suite v3.0 - Offline Edition");
        Console.WriteLine("====================================================");
        Console.WriteLine();
        Console.WriteLine("  Starting server...");
        Console.WriteLine("  URL: http://localhost:8000");
        Console.WriteLine();
        Console.WriteLine("  DO NOT close this window while using the app.");
        Console.WriteLine("====================================================");

        // Open browser after delay
        new Thread(() =>
        {
            Thread.Sleep(2500);
            try { Process.Start(new ProcessStartInfo("http://localhost:8000") { UseShellExecute = true }); }
            catch { }
        }).Start();

        // Start uvicorn server
        var psi = new ProcessStartInfo
        {
            FileName = pythonExe,
            Arguments = "-m uvicorn api:app --host 127.0.0.1 --port 8000",
            WorkingDirectory = appDir,
            UseShellExecute = false
        };
        
        try
        {
            var proc = Process.Start(psi);
            proc.WaitForExit();
        }
        catch (Exception ex)
        {
            Console.WriteLine("ERROR: " + ex.Message);
            Console.WriteLine("Press any key to exit...");
            Console.ReadKey();
        }
    }
}
