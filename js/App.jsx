import React from 'react';
import { useEffect, useState } from 'react';

export default function App() {
	const [selectedStage, setSelectedStage] = useState(null);
	const [eventInfo, setEventInfo] = useState(null);
	const [teams, setTeams] = useState(null);

	useEffect(async () => {
		setEventInfo(await (await fetch('/bloudeni/event.json')).json());
		setTeams(await (await fetch('/bloudeni/teams.json')).json());
	}, []);

	if (eventInfo === null) {
		return (
			<p>Loading eventInfo…</p>
		);
	}
	if (selectedStage === null) {
		return Object.entries(eventInfo.stages).map(([id, stage]) => <button key={id} onClick={() => setSelectedStage(id)}>{stage.short}</button>);
	}

	if (teams === null) {
		return (
			<p>Loading teams…</p>
		);
	}
	return (
		<table>
			<thead>
				<tr>
					<th>ID</th>
					<th>Tým</th>
					<th>Gender</th>
					<th>Age</th>
					<th>Čip</th>
					<th>Member1</th>
					<th>Member2</th>
					<th>Čas</th>
					<th>Trestné minuty</th>
					<th>Trestné body</th>
					<th>Získané body</th>
					<th>Celk. body</th>
				</tr>
			</thead>
			<tbody>
				{teams.map((team) => {
					<React.Fragment>
						<tr>
							<td>{team.id}</td>
							<td>{team.name}</td>
							<td>{team.gender}</td>
							<td>{team.age}</td>
							<td>{team.si}</td>
							<td>{team.member1}</td>
							<td>{team.member2}</td>
							<td>{team.time}</td>
							<td>{team.penaltyTime}</td>
							<td>{team.penaltyPoints}</td>
							<td>{team.gainedPoints}</td>
							<td>{team.finalPoints}</td>
						</tr>
					</React.Fragment>
				})}
			</tbody>
		</table>
	);
}
