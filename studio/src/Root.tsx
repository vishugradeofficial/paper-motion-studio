import React from 'react';
import {Composition} from 'remotion';
import {Reel,Project} from './Reel';
import sample from '../../examples/one-clear-idea/project.json';
export const Root=()=> <Composition id="PaperReel" component={Reel} defaultProps={{project:sample as Project}} width={1080} height={1920} fps={30} durationInFrames={1080} calculateMetadata={({props})=>({width:props.project.width,height:props.project.height,fps:props.project.fps,durationInFrames:Math.round(props.project.duration*props.project.fps)})}/>;
