import Foundation

struct AppleHealthManifest: Codable {
    static let schemaVersion = "crow-health.apple-health-manifest.v1"

    let schemaVersion: String
    let generatedAt: Date
    let types: [HealthTypeManifest]

    init(generatedAt: Date, types: [HealthTypeManifest]) {
        self.schemaVersion = Self.schemaVersion
        self.generatedAt = generatedAt
        self.types = types.sorted { $0.identifier < $1.identifier }
    }
}

struct HealthTypeManifest: Codable, Identifiable {
    var id: String { identifier }

    let identifier: String
    let sampleCount: Int
    let firstObservedAt: Date?
    let lastObservedAt: Date?
    let units: [String]
    let sources: [HealthSourceManifest]
}

struct HealthSourceManifest: Codable, Hashable {
    let name: String
    let bundleIdentifier: String
    let sampleCount: Int
}
