@{
    Root = 'c:\Users\cedri\Documents\PycharmProjects\JeanClaudeCompagnon\run.ps1'
    OutputPath = 'c:\Users\cedri\Documents\PycharmProjects\JeanClaudeCompagnon\out'
    Package = @{
        Enabled = $true
        Obfuscate = $false
        HideConsoleWindow = $false
        DotNetVersion = 'v4.6.2'
        FileVersion = '1.0.0'
        FileDescription = ''
        ProductName = ''
        ProductVersion = ''
        Copyright = ''
        RequireElevation = $false
        ApplicationIconPath = ''
        PackageType = 'Console'
    }
    Bundle = @{
        Enabled = $true
        Modules = $true
        # IgnoredModules = @()
    }
}
        