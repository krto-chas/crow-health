import SwiftUI

struct ContentView: View {
    @EnvironmentObject private var model: CollectorViewModel
    @State private var exportURL: URL?

    var body: some View {
        NavigationStack {
            List {
                Section("Status") {
                    Text(model.status)
                    if let errorMessage = model.errorMessage {
                        Text(errorMessage)
                            .foregroundStyle(.red)
                    }
                }

                Section("Collection") {
                    Button("Authorize and build manifest") {
                        Task {
                            await model.authorizeAndCollect()
                            exportURL = try? model.exportFile()
                        }
                    }
                    .disabled(model.isWorking)

                    if model.isWorking {
                        ProgressView()
                    }
                }

                if let manifest = model.manifest {
                    Section("Accessible HealthKit types") {
                        ForEach(manifest.types) { type in
                            VStack(alignment: .leading, spacing: 4) {
                                Text(type.identifier)
                                    .font(.headline)
                                Text("Samples: \(type.sampleCount)")
                                Text("Sources: \(type.sources.count)")
                                if !type.units.isEmpty {
                                    Text("Units: \(type.units.joined(separator: ", "))")
                                }
                            }
                        }
                    }
                }

                if let exportURL {
                    Section("Export") {
                        ShareLink(item: exportURL) {
                            Label("Share value-free manifest", systemImage: "square.and.arrow.up")
                        }
                    }
                }
            }
            .navigationTitle("Crow Health Collector")
        }
    }
}
