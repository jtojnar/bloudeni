import React from 'react';
import { useEffect, useState } from 'react';

function useJsonData(url) {
	const [data, setData] = useState(null);

	useEffect(() => {
		if (url) {
			let ignore = false;

			fetch(url)
				.then(response => response.json())
				.then(json => {
					if (!ignore) {
						setData(json);
					}
				});

			return () => {
				ignore = true;
			};
		}
	}, [url]);

	return data;
}

export default function App() {
	const [selectedStage, setSelectedStage] = useState(null);
	const eventInfo = useJsonData('/bloudeni/event.json');
	const teams = useJsonData('/bloudeni/teams.json')

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
