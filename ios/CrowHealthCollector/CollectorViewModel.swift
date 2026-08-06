import Foundation

@MainActor
final class CollectorViewModel: ObservableObject {
    @Published private(set) var manifest: AppleHealthManifest?
    @Published private(set) var status = "Not authorized"
    @Published private(set) var isWorking = false
    @Published var errorMessage: String?

    private let collector = HealthKitManifestCollector()

    func authorizeAndCollect() async {
        isWorking = true
        errorMessage = nil
        defer { isWorking = false }

        do {
            status = "Requesting Health access"
            try await collector.requestAuthorization()
            status = "Inventorying accessible samples"
            manifest = try await collector.collectManifest()
            status = "Manifest ready"
        } catch {
            status = "Collection failed"
            errorMessage = error.localizedDescription
        }
    }

    func exportFile() throws -> URL {
        guard let manifest else { throw CollectorError.noManifest }
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys, .withoutEscapingSlashes]
        encoder.dateEncodingStrategy = .iso8601
        let data = try encoder.encode(manifest)
        let url = FileManager.default.temporaryDirectory
            .appendingPathComponent("apple_health_manifest.json")
        try data.write(to: url, options: .atomic)
        return url
    }
}
