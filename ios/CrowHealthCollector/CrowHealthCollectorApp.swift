import SwiftUI

@main
struct CrowHealthCollectorApp: App {
    @StateObject private var model = CollectorViewModel()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(model)
        }
    }
}
