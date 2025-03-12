from fontTools import ttLib
from fontTools.pens.recordingPen import RecordingPen
import argparse
import os

def has_visible_contours(glyph, font):
    """グリフが見える輪郭を持っているかチェック"""
    if hasattr(glyph, 'numberOfContours') and glyph.numberOfContours > 0:
        return True
    
    # TTグリフの場合、描画してみて命令があるか確認
    pen = RecordingPen()
    try:
        glyph.draw(pen, font['glyf'])  # glyfTableを引数として渡す
        return len(pen.value) > 0
    except (AttributeError, NotImplementedError, TypeError):
        pass
    
    # 複合グリフの場合
    if hasattr(glyph, "components") and len(glyph.components) > 0:
        return True
    
    return False

def is_empty_glyph(glyph_name, font):
    """空のグリフかどうかを判定する"""
    if glyph_name not in font['glyf'].glyphs:
        return True
    
    glyph = font['glyf'][glyph_name]
    return not has_visible_contours(glyph, font)  # フォントオブジェクトを渡す

def cleanup_font(input_path, output_path, new_font_name=None):
    """フォントを読み込み、空のグリフを削除して保存する"""
    print(f"入力フォント: {input_path}")
    font = ttLib.TTFont(input_path)
    
    # 文字コードとグリフ名のマッピングを取得
    cmap = font.getBestCmap()
    
    # 空でないグリフを持つ文字コードだけを残す
    valid_chars = {}
    removed_count = 0
    
    for char_code, glyph_name in cmap.items():
        if not is_empty_glyph(glyph_name, font):
            valid_chars[char_code] = glyph_name
        else:
            removed_count += 1
    
    print(f"空のグリフ数: {removed_count}")
    print(f"有効なグリフ数: {len(valid_chars)}")
    
    # cmapテーブルを再構成
    for table in font['cmap'].tables:
        table.cmap = {k: v for k, v in table.cmap.items() if k in valid_chars}
    
    # フォント名を変更（オプション）
    if new_font_name:
        for name_record in font['name'].names:
            if name_record.nameID in (1, 4, 6):  # フォント名関連のID
                old_name = name_record.toUnicode()
                # 新しい名前を追加
                new_name = f"{new_font_name}"
                if name_record.nameID == 6:  # PostScript名は空白を含めない
                    new_name = new_name.replace(' ', '')
                name_record.string = new_name.encode('utf-16-be') if name_record.platformID == 0 or name_record.platformID == 3 else new_name
                print(f"フォント名を変更: {old_name} -> {new_name}")
    
    # 新しいフォントを保存
    font.save(output_path)
    print(f"出力フォント: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TTFフォントから空のグリフを削除し再構成します")
    parser.add_argument("input_font", help="入力TTFファイルのパス")
    parser.add_argument("output_font", nargs="?", help="出力TTFファイルのパス（省略時は自動生成）")
    parser.add_argument("--name", help="新しいフォント名（省略可）")
    
    args = parser.parse_args()
    
    input_path = args.input_font
    output_path = args.output_font
    
    if not output_path:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_cleaned{ext}"
    
    cleanup_font(input_path, output_path, args.name)