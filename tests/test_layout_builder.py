import pytest
from app.schemas import ComicPanelOutline, ComicPanelStory
from app.services.layout_builder import LayoutBuildError, build_comic_layout


def outlines(order=(1,2,3,4,5)):
    return [ComicPanelOutline(panel_number=i,title=f"Title {i}",scene_description=f"Scene {i}",image_prompt=f"Img {i}") for i in order]

def stories(order=(1,2,3,4,5)):
    return [ComicPanelStory(panel_number=i,narration=f"Narr {i}",dialogue=f"Dlg {i}") for i in order]

def images():
    return {i:f"/static/panels/{i}.png" for i in range(1,6)}


def test_unordered_inputs_are_sorted_and_paired_by_panel_number():
    result = build_comic_layout(outlines((5,3,1,4,2)), stories((2,5,4,1,3)), images())
    assert [p.panel_number for p in result] == [1,2,3,4,5]
    assert result[2].title == "Title 3"
    assert result[2].narration == "Narr 3"
    assert result[2].image_path.endswith("3.png")


def test_missing_story_raises_clear_error():
    with pytest.raises(LayoutBuildError):
        build_comic_layout(outlines(), stories((1,2,3,4)), images())


def test_placeholder_is_a_valid_image_path():
    paths = images(); paths[4] = "/static/placeholders/panel-placeholder.png"
    result = build_comic_layout(outlines(), stories(), paths)
    assert len(result) == 5
    assert result[3].image_path.endswith("panel-placeholder.png")
