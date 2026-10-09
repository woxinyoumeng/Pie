//
//  IconsaxIcon.swift
//  PiCode
//
//  Iconsax (Linear) icon rendering. The used glyphs are vendored as template
//  SVGs under Assets.xcassets/Iconsax, so they tint with the surrounding
//  foreground style.
//

import AppKit
import SwiftUI

/// An Iconsax glyph drawn at a consistent, Dynamic Type-aware size.
struct IconsaxIcon: View {
    var name: String
    /// Overrides the default size for large decorative glyphs (empty states).
    var size: CGFloat?

    @ScaledMetric(relativeTo: .body) private var scaledSize: CGFloat = 14

    var body: some View {
        iconsaxImage(name)
            .resizable()
            .scaledToFit()
            .frame(width: size ?? scaledSize, height: size ?? scaledSize)
    }
}

/// The Iconsax glyph as an `Image`. The vendored assets carry an intrinsic size,
/// so this also works inline in `Text` and as a `Label` icon AppKit draws into a
/// menu.
func iconsaxImage(_ name: String) -> Image {
    Image("Iconsax/\(name)")
}

extension Label where Title == Text, Icon == Image {
    init(_ titleKey: LocalizedStringKey, iconsax name: String) {
        self.init { Text(titleKey) } icon: { iconsaxImage(name) }
    }

    /// `String` 版本必须显式经过 `L(_:)`。
    ///
    /// 字面量在重载解析里会命中这个泛型重载(而不是 `LocalizedStringKey` 那个,
    /// 实验已证实:`Label("New chat", iconsax:)` 走的是这里),而 `Text(String)`
    /// 不做本地化查找 —— 菜单项因此一直是英文。
    init<S: StringProtocol>(_ title: S, iconsax name: String) {
        self.init { Text(L(String(title))) } icon: { iconsaxImage(name) }
    }
}

extension NSImage {
    /// The Iconsax glyph as an `NSImage`, for AppKit surfaces such as menus.
    static func iconsax(_ name: String) -> NSImage {
        let image = NSImage(named: "Iconsax/\(name)") ?? NSImage()
        image.isTemplate = true
        return image
    }
}
