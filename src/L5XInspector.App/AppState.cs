namespace L5XInspector.App;

using System.Collections.ObjectModel;
using L5XInspector.Core;
using L5XInspector.Core.Models;

public static class AppState
{
    public static string StationRulesFileName { get; set; } = "Loaded file: (none)";
    public static string L5xFileName { get; set; } = "Loaded file: (none)";

    public static ObservableCollection<AoiUdtItem> AoiUdtItems { get; } = new();

    public static ObservableCollection<ImpactItem> ImpactItems { get; } = new();

    public static ImpactSummary Impact { get; private set; } = new(0, 0, 0, 0);

    public static void LoadProject(ProjectIr project)
    {
        AoiUdtItems.Clear();
        foreach (var aoi in project.Aois)
        {
            AoiUdtItems.Add(new AoiUdtItem(
                "AOI",
                aoi.Name,
                aoi.Description ?? "Add-on instruction",
                $"Routines: {aoi.Routines.Count}"));
        }

        foreach (var udt in project.DataTypes)
        {
            AoiUdtItems.Add(new AoiUdtItem(
                "UDT",
                udt.Name,
                udt.Description ?? "User-defined type",
                $"Members: {udt.Members.Count}"));
        }

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
    }
}

public sealed record AoiUdtItem(string Kind, string Name, string Summary, string Meta);

public sealed record ImpactSummary(int Tags, int Stations, int Aois, int Paths);

public sealed record ImpactItem(string Name, string Meta, string Detail);
