//
//  PaletteCommand.swift
//  PiCode
//
//  The single list of actions that menus, keyboard shortcuts, and the command
//  palette all share. Views own the dispatch (they have the focused controls);
//  this file only names the actions and their presentation.
//

import Foundation

enum PaletteCommand: String, CaseIterable, Identifiable, Hashable {
    case newSession
    case addProject
    case refreshSessions
    case renameSession
    case cloneSession
    case forkLatest
    case compactContext
    case compactWithInstructions
    case exportSession
    case deleteSession

    case focusComposer
    case interrupt
    case abortRun
    case cycleModel
    case cycleThinkingLevel

    case toggleInspector
    case toggleSidebar
    case toggleTerminal

    case copyTranscript
    case copyLastResponse
    case openInTerminal
    case openInVSCode
    case revealInFinder
    case revealPiDirectory

    case openSettings
    case providersSettings
    case packages
    case showPiSetup
    case checkForPiUpdates

    var id: String { rawValue }

    var title: String {
        switch self {
        case .newSession: return L("New Session")
        case .addProject: return L("Open Project Folder…")
        case .refreshSessions: return L("Reload Sessions")
        case .renameSession: return L("Rename Session…")
        case .cloneSession: return L("Clone Current Branch")
        case .forkLatest: return L("Fork…")
        case .compactContext: return L("Compact Context")
        case .compactWithInstructions: return L("Compact with Instructions…")
        case .exportSession: return L("Export Session as HTML…")
        case .deleteSession: return L("Delete Session…")
        case .focusComposer: return L("Focus Composer")
        case .interrupt: return L("Interrupt and Restore Queue")
        case .abortRun: return L("Stop the Agent")
        case .cycleModel: return L("Cycle Model")
        case .cycleThinkingLevel: return L("Cycle Thinking Level")
        case .toggleInspector: return L("Toggle Inspector")
        case .toggleSidebar: return L("Toggle Sidebar")
        case .toggleTerminal: return L("Toggle Terminal")
        case .copyTranscript: return L("Copy Transcript")
        case .copyLastResponse: return L("Copy Last Response")
        case .openInTerminal: return L("Open Project in Terminal")
        case .openInVSCode: return L("Open Project in VS Code")
        case .revealInFinder: return L("Reveal Project in Finder")
        case .revealPiDirectory: return L("Reveal Pi's Config Folder")
        case .openSettings: return L("Settings…")
        case .providersSettings: return L("Providers and Credentials…")
        case .packages: return L("Packages")
        case .showPiSetup: return L("Pi Setup Help")
        case .checkForPiUpdates: return L("Check Pi Version")
        }
    }

    var systemImage: String {
        switch self {
        case .newSession: return "message-add"
        case .addProject: return "folder-add"
        case .refreshSessions: return "refresh"
        case .renameSession: return "edit-2"
        case .cloneSession: return "document-copy"
        case .forkLatest: return "hierarchy-2"
        case .compactContext, .compactWithInstructions: return "convert"
        case .exportSession: return "export"
        case .deleteSession: return "trash"
        case .focusComposer: return "edit-2"
        case .interrupt: return "stop"
        case .abortRun: return "stop-circle"
        case .cycleModel: return "cpu"
        case .cycleThinkingLevel: return "lamp-on"
        case .toggleInspector: return "sidebar-right"
        case .toggleSidebar: return "sidebar-left"
        case .toggleTerminal: return "command-square"
        case .copyTranscript: return "clipboard-text"
        case .copyLastResponse: return "tick-circle"
        case .openInTerminal: return "command-square"
        case .openInVSCode: return "code"
        case .revealInFinder: return "folder"
        case .revealPiDirectory: return "setting-3"
        case .openSettings: return "setting-2"
        case .providersSettings: return "key"
        case .packages: return "box"
        case .showPiSetup: return "message-question"
        case .checkForPiUpdates: return "refresh-circle"
        }
    }

    /// Actions that only make sense with a live session.
    var requiresSession: Bool {
        switch self {
        case .newSession, .addProject, .refreshSessions, .toggleInspector, .toggleSidebar,
             .toggleTerminal, .openSettings, .providersSettings, .packages, .showPiSetup,
             .checkForPiUpdates, .revealPiDirectory:
            return false
        default:
            return true
        }
    }

    /// Actions that require Pi to be idle.
    var requiresIdleAgent: Bool {
        switch self {
        case .compactContext, .compactWithInstructions, .deleteSession, .renameSession,
             .cloneSession, .forkLatest, .exportSession, .newSession:
            return true
        default:
            return false
        }
    }

    var shortcutHint: String? {
        switch self {
        case .newSession: return "⌘N"
        case .addProject: return "⇧⌘O"
        case .refreshSessions: return "⌘R"
        case .renameSession: return "⇧⌘R"
        case .compactContext: return "⌘K"
        case .exportSession: return "⇧⌘E"
        case .focusComposer: return "⌘L"
        case .interrupt: return "esc"
        case .abortRun: return "⌘."
        case .toggleInspector: return "⌥⌘I"
        case .toggleSidebar: return "⌃⌘S"
        case .toggleTerminal: return "⌃`"
        case .openSettings: return "⌘,"
        case .openInTerminal: return "⇧⌘T"
        default: return nil
        }
    }

    var group: Group {
        switch self {
        case .newSession, .addProject, .refreshSessions, .renameSession, .cloneSession,
             .forkLatest, .compactContext, .compactWithInstructions, .exportSession, .deleteSession:
            return .session
        case .focusComposer, .interrupt, .abortRun, .cycleModel, .cycleThinkingLevel:
            return .run
        case .toggleInspector, .toggleSidebar, .toggleTerminal, .packages:
            return .view
        case .copyTranscript, .copyLastResponse, .openInTerminal, .openInVSCode, .revealInFinder,
             .revealPiDirectory:
            return .share
        case .openSettings, .providersSettings, .showPiSetup, .checkForPiUpdates:
            return .app
        }
    }

    enum Group: String, CaseIterable, Identifiable {
        case session
        case run
        case view
        case share
        case app

        var id: String { rawValue }

        var label: String {
            switch self {
            case .session: return L("Session")
            case .run: return L("Agent")
            case .view: return L("View")
            case .share: return L("Share")
            case .app: return "PiCode"
            }
        }
    }
}
