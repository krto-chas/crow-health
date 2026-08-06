import Foundation
import HealthKit

actor HealthKitManifestCollector {
    private let healthStore: HKHealthStore

    init(healthStore: HKHealthStore = HKHealthStore()) {
        self.healthStore = healthStore
    }

    static var readableTypes: [HKSampleType] {
        let identifiers: [HKQuantityTypeIdentifier] = [
            .heartRate,
            .restingHeartRate,
            .stepCount,
            .activeEnergyBurned,
            .bodyMass,
        ]
        var types = identifiers.compactMap(HKObjectType.quantityType(forIdentifier:))
        if let sleep = HKObjectType.categoryType(forIdentifier: .sleepAnalysis) {
            types.append(sleep)
        }
        return types.sorted { $0.identifier < $1.identifier }
    }

    func requestAuthorization() async throws {
        guard HKHealthStore.isHealthDataAvailable() else {
            throw CollectorError.healthDataUnavailable
        }
        try await healthStore.requestAuthorization(toShare: [], read: Set(Self.readableTypes))
    }

    func collectManifest() async throws -> AppleHealthManifest {
        var manifests: [HealthTypeManifest] = []
        for type in Self.readableTypes {
            let samples = try await samples(for: type)
            manifests.append(manifest(for: type, samples: samples))
        }
        return AppleHealthManifest(generatedAt: Date(), types: manifests)
    }

    private func samples(for type: HKSampleType) async throws -> [HKSample] {
        try await withCheckedThrowingContinuation { continuation in
            let sort = NSSortDescriptor(key: HKSampleSortIdentifierStartDate, ascending: true)
            let query = HKSampleQuery(
                sampleType: type,
                predicate: nil,
                limit: HKObjectQueryNoLimit,
                sortDescriptors: [sort]
            ) { _, samples, error in
                if let error {
                    continuation.resume(throwing: error)
                    return
                }
                continuation.resume(returning: samples ?? [])
            }
            healthStore.execute(query)
        }
    }

    private func manifest(for type: HKSampleType, samples: [HKSample]) -> HealthTypeManifest {
        var sources: [HealthSourceManifest: Int] = [:]
        var units = Set<String>()

        for sample in samples {
            let source = HealthSourceManifest(
                name: sample.sourceRevision.source.name,
                bundleIdentifier: sample.sourceRevision.source.bundleIdentifier,
                sampleCount: 0
            )
            sources[source, default: 0] += 1
            if let quantity = sample as? HKQuantitySample,
               let unit = preferredUnit(for: quantity.quantityType) {
                units.insert(unit.unitString)
            }
        }

        let sourceRows = sources.map { source, count in
            HealthSourceManifest(
                name: source.name,
                bundleIdentifier: source.bundleIdentifier,
                sampleCount: count
            )
        }.sorted {
            ($0.bundleIdentifier, $0.name) < ($1.bundleIdentifier, $1.name)
        }

        return HealthTypeManifest(
            identifier: type.identifier,
            sampleCount: samples.count,
            firstObservedAt: samples.first?.startDate,
            lastObservedAt: samples.last?.endDate,
            units: units.sorted(),
            sources: sourceRows
        )
    }

    private func preferredUnit(for type: HKQuantityType) -> HKUnit? {
        switch type.identifier {
        case HKQuantityTypeIdentifier.heartRate.rawValue,
             HKQuantityTypeIdentifier.restingHeartRate.rawValue:
            return HKUnit.count().unitDivided(by: .minute())
        case HKQuantityTypeIdentifier.stepCount.rawValue:
            return .count()
        case HKQuantityTypeIdentifier.activeEnergyBurned.rawValue:
            return .kilocalorie()
        case HKQuantityTypeIdentifier.bodyMass.rawValue:
            return .gramUnit(with: .kilo)
        default:
            return nil
        }
    }
}

enum CollectorError: LocalizedError {
    case healthDataUnavailable
    case noManifest

    var errorDescription: String? {
        switch self {
        case .healthDataUnavailable:
            return "Health data is unavailable on this device."
        case .noManifest:
            return "Generate a manifest before exporting."
        }
    }
}
