from __future__ import annotations

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app import models  # noqa: F401
from app.models import User
from app.services import invite_graph_service, user_attribute_service


@pytest.fixture(name="session")
def session_fixture() -> Session:
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def create_user(session: Session, username: str) -> User:
    user = User(username=username, is_admin=False)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def link_invite(session: Session, invitee: User, inviter: User) -> None:
    user_attribute_service.set_attribute(
        session,
        user_id=invitee.id,
        key=user_attribute_service.INVITED_BY_USER_ID_KEY,
        value=str(inviter.id),
        actor_user_id=inviter.id,
    )
    session.commit()


def test_build_invite_graph_three_degrees(session: Session) -> None:
    root = create_user(session, "root")
    first_a = create_user(session, "first-a")
    first_b = create_user(session, "first-b")
    second_a = create_user(session, "second-a")
    third_a = create_user(session, "third-a")

    link_invite(session, first_a, root)
    link_invite(session, first_b, root)
    link_invite(session, second_a, first_a)
    link_invite(session, third_a, second_a)

    graph = invite_graph_service.build_invite_graph(session, root_user_id=root.id)

    assert graph is not None
    assert graph.degree == 0
    assert {child.username for child in graph.children} == {"first-a", "first-b"}

    first_a_node = next(node for node in graph.children if node.username == "first-a")
    assert first_a_node.degree == 1
    assert [child.username for child in first_a_node.children] == ["second-a"]

    second_a_node = first_a_node.children[0]
    assert second_a_node.degree == 2
    assert [child.username for child in second_a_node.children] == ["third-a"]
    assert second_a_node.children[0].degree == 3


def test_build_invite_graph_respects_max_degree(session: Session) -> None:
    root = create_user(session, "root")
    first = create_user(session, "first")
    second = create_user(session, "second")

    link_invite(session, first, root)
    link_invite(session, second, first)

    graph = invite_graph_service.build_invite_graph(session, root_user_id=root.id, max_degree=1)

    assert graph is not None
    assert len(graph.children) == 1
    assert graph.children[0].username == "first"
    assert graph.children[0].children == []
