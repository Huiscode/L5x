namespace L5XInspector.App;

using System.Collections.ObjectModel;
using L5XInspector.Core;
using L5XInspector.Core.Models;

public static class AppState
{
    public static string StationRulesFileName { get; set; } = "Loaded file: (none)";
    public static string L5xFileName { get; set; } = "Loaded file: (none)";

    public static ObservableCollection<AoiUdtItem> AoiUdtItems { get; } = new();
    public static List<AoiUdtItem> AoiUdtItemsAll { get; } = new();

    public static ObservableCollection<ImpactItem> ImpactItems { get; } = new();
    public static ObservableCollection<ImpactFlowItem> ImpactFlows { get; } = new();

    public static ImpactSummary Impact { get; private set; } = new(0, 0, 0, 0);

    public static void LoadProject(ProjectIr project)
    {
        AoiUdtItems.Clear();
        AoiUdtItemsAll.Clear();

        var controllerTags = project.ControllerTags.Count;
        var programTags = project.Programs.Sum(p => p.ProgramTags.Count);

        foreach (var aoi in project.Aois.OrderBy(a => a.Name))
        {
            AoiUdtItemsAll.Add(new AoiUdtItem(
                "AOI",
                aoi.Name,
                CleanDescription(aoi.Description) ?? "Add-on instruction",
                $"Routines: {aoi.Routines.Count}",
                ParameterCount: aoi.Parameters.Count,
                RoutineCount: aoi.Routines.Count));
        }

        foreach (var udt in project.DataTypes.OrderBy(d => d.Name))
        {
            var members = udt.Members.Count;
            var summary = CleanDescription(udt.Description) ?? "User-defined type";
            if (members == 0)
                summary = "User-defined type (members not exported)";

            AoiUdtItemsAll.Add(new AoiUdtItem(
                "UDT",
                udt.Name,
                summary,
                $"Members: {members}",
                MemberCount: members));
        }

        ApplyAoiUdtFilter("All");

        var graph = DependencyGraphBuilder.Build(project);
        var uniqueTags = project.Programs
            .SelectMany(p => p.Routines)
            .SelectMany(r => r.ReadTags.Concat(r.WriteTags))
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .Count();

        var stations = graph.Nodes.Values.Count(n => n.Kind == GraphNodeKind.Station);
        var aois = project.Aois.Count;
        var paths = graph.EdgeCount;

        Impact = new ImpactSummary(uniqueTags, stations, aois, paths);

        ImpactItems.Clear();
        var topTags = project.Programs
            .SelectMany(p => p.Routines)
            .SelectMany(r => r.WriteTags)
            .GroupBy(t => t, StringComparer.OrdinalIgnoreCase)
            .OrderByDescending(g => g.Count())
            .Take(5)
            .Select(g => new ImpactItem($"Tag: {g.Key}", $"Writes: {g.Count()}", "Potential downstream impacts"));

        foreach (var item in topTags)
            ImpactItems.Add(item);

        if (ImpactItems.Count == 0)
        {
            ImpactItems.Add(new ImpactItem("No impacts detected", "", ""));
        }

        ImpactFlows.Clear();
        var flowSamples = project.Programs
            .SelectMany(p => p.Routines)
            .SelectMany(r => r.WriteTags.Select(t => (Routine: r.Name, Tag: t)))
            .Take(8)
            .Select(pair => new ImpactFlowItem(
                Source: pair.Routine,
                Tag: pair.Tag,
                Target: "Downstream"));

        foreach (var flow in flowSamples)
            ImpactFlows.Add(flow);

        if (ImpactFlows.Count == 0)
            ImpactFlows.Add(new ImpactFlowItem("N/A", "No writes found", ""));

        AoiUdtItemsAll.Add(new AoiUdtItem(
            "INFO",
            "Tag Inventory",
            $"Controller tags: {controllerTags}",
            $"Program tags: {programTags}"));
    }

    public static void ApplyAoiUdtFilter(string filter)
    {
        AoiUdtItems.Clear();
        IEnumerable<AoiUdtItem> source = AoiUdtItemsAll;

        if (string.Equals(filter, "AOI", StringComparison.OrdinalIgnoreCase))
            source = source.Where(i => i.Kind == "AOI");
        else if (string.Equals(filter, "UDT", StringComparison.OrdinalIgnoreCase))
            source = source.Where(i => i.Kind == "UDT");
        else if (string.Equals(filter, "TAGS", StringComparison.OrdinalIgnoreCase))
            source = source.Where(i => i.Kind == "INFO");

        foreach (var item in source)
            AoiUdtItems.Add(item);
    }

    private static string? CleanDescription(string? raw)
    {
        if (string.IsNullOrWhiteSpace(raw))
            return null;

        var trimmed = raw.Trim();
        if (trimmed.StartsWith("<![CDATA[", StringComparison.OrdinalIgnoreCase))
            trimmed = trimmed.Replace("<![CDATA[", string.Empty, StringComparison.OrdinalIgnoreCase)
                             .Replace("]]>", string.Empty, StringComparison.OrdinalIgnoreCase)
                             .Trim();

        return System.Text.RegularExpressions.Regex.Replace(trimmed, "<[^>]+>", string.Empty)
            .Replace("\r", " ")
            .Replace("\n", " ")
            .Trim();
    }
}

public sealed record AoiUdtItem(
    string Kind,
    string Name,
    string Summary,
    string Meta,
    int ParameterCount = 0,
    int MemberCount = 0,
    int RoutineCount = 0);

public sealed record ImpactSummary(int Tags, int Stations, int Aois, int Paths);

public sealed record ImpactItem(string Name, string Meta, string Detail);

public sealed record ImpactFlowItem(string Source, string Tag, string Target);
