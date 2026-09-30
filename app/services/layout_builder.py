from __future__ import annotations

from app.schemas import ComicPanelLayout, ComicPanelOutline, ComicPanelStory


class LayoutBuildError(RuntimeError):
    pass


def build_comic_layout(
    outline: list[ComicPanelOutline],
    stories: list[ComicPanelStory],
    image_paths: dict[int, str],
) -> list[ComicPanelLayout]:
    expected = {1, 2, 3, 4, 5}
    outline_map = {p.panel_number: p for p in outline}
    story_map = {p.panel_number: p for p in stories}
    if set(outline_map) != expected:
        raise LayoutBuildError("Outline data must contain panels 1 through 5.")
    if set(story_map) != expected:
        raise LayoutBuildError("Story data must contain panels 1 through 5.")
    if set(image_paths) != expected:
        raise LayoutBuildError("Image data must contain panels 1 through 5.")

    result: list[ComicPanelLayout] = []
    for number in range(1, 6):
        o = outline_map[number]
        s = story_map[number]
        result.append(
            ComicPanelLayout(
                panel_number=number,
                title=o.title,
                scene_description=o.scene_description,
                narration=s.narration,
                dialogue=s.dialogue,
                image_path=image_paths[number],
            )
        )
    return result
