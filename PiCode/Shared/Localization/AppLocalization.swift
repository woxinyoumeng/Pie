//
//  AppLocalization.swift
//  PiCode
//
//  界面语言的字符串查找入口。
//
//  SwiftUI 的字面量(`Text("Settings…")`、`Button("Cancel")`、`.help("…")`)
//  由根视图上的 `.environment(\.locale, …)` 驱动,不需要经过本文件。
//  这里服务的是 `String` 上下文:枚举的 `var title: String`、窗口标题、
//  菜单项标题,以及任何无法写成 `LocalizedStringKey` 的位置。
//

import Foundation

/// `String` 上下文的本地化查找。
///
/// 实现有意保持无状态:`L(_:)` 每次调用都重新解析当前语言,所以设置界面
/// 切换语言之后,下一次视图求值就会拿到新文案,不需要重启应用。
enum AppLocalization {
    /// 英文是开发语言,译文的源字符串就是英文,因此没有 `en.lproj`。
    static let developmentLanguageIdentifier = "en"

    /// 取出 `key` 在当前语言下的文案;没有译文时回退为 `key` 本身。
    static func string(_ key: String) -> String {
        let identifier = PreferencesStore.AppLanguage.current.resolvedIdentifier
        let bundlePath = Bundle.main.path(forResource: identifier, ofType: "lproj")
        guard identifier != developmentLanguageIdentifier,
              let bundlePath,
              let bundle = Bundle(path: bundlePath)
        else {
            return key
        }
        return bundle.localizedString(forKey: key, value: key, table: nil)
    }
}

/// 与前端 i18n 的 `t("…")` 同义,便于在 `String` 上下文里一眼认出可翻译文案。
func L(_ key: String) -> String {
    AppLocalization.string(key)
}
